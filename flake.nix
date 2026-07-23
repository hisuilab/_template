{
  description = "Project template generator";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    git-hooks.url = "github:cachix/git-hooks.nix";
    git-hooks.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      treefmt-nix,
      git-hooks,
      ...
    }:
    let
      systems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pkgsFor = system: nixpkgs.legacyPackages.${system};
      treefmtEval = forAllSystems (system: treefmt-nix.lib.evalModule (pkgsFor system) ./treefmt.nix);
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
        in
        {
          default = pkgs.writeShellApplication {
            name = "_template";
            runtimeInputs = [ (pkgs.python3.withPackages (ps: [ ps.questionary ])) ];
            text = ''
              PYTHONPATH="${self}" TEMPLATE_ROOT="${self}/template" python3 -m tooling.generator "$@"
            '';
          };
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/_template";
        };
      });

      formatter = forAllSystems (system: treefmtEval.${system}.config.build.wrapper);

      devShells = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
          hooks = git-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              # ── フォーマット（Nix / TOML / JSON / YAML / Python / shell）──
              treefmt = {
                enable = true;
                package = treefmtEval.${system}.config.build.wrapper;
              };

              # ── Markdown lint / fix ──
              rumdl = {
                enable = true;
                entry = "${pkgs.rumdl}/bin/rumdl check --fix --config rumdl.toml";
                types = [ "markdown" ];
              };

              # ── シークレット検出 ──
              gitleaks = {
                enable = true;
                name = "Detect secrets with gitleaks";
                entry = "${pkgs.gitleaks}/bin/gitleaks protect --staged --redact --config .gitleaks.toml";
                pass_filenames = false;
              };

              # ── プロジェクト固有チェック ──
              check-readme = {
                enable = true;
                name = "Require README.md (概要/責任) in every owned directory";
                entry = "./scripts/check-readme";
                pass_filenames = false;
              };

              check-status = {
                enable = true;
                name = "Validate status frontmatter in docs/";
                entry = "./scripts/check-status";
                pass_filenames = false;
              };

              check-encoding = {
                enable = true;
                name = "Detect U+FFFD replacement characters";
                entry = "./scripts/check-encoding";
                pass_filenames = false;
              };

              # ── Conventional Commits（commit-msg ステージ）──
              convco = {
                enable = true;
                stages = [ "commit-msg" ];
              };
            };
          };
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.bats
              pkgs.gh
              pkgs.git
              pkgs.gitleaks
              pkgs.jq
              pkgs.just
              pkgs.nixd
              pkgs.python3
              pkgs.python3Packages.pytest
              pkgs.python3Packages.questionary
              pkgs.ripgrep
              pkgs.ruff
              pkgs.rumdl
              pkgs.shellcheck
              pkgs.shfmt
              treefmtEval.${system}.config.build.wrapper
            ];

            shellHook = hooks.shellHook;
          };
        }
      );
    };
}
