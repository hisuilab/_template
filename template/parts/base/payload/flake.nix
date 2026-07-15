{
  description = "{{project_name}}";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    git-hooks.url = "github:cachix/git-hooks.nix";
    git-hooks.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
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
      formatter = forAllSystems (system: treefmtEval.${system}.config.build.wrapper);

      devShells = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
          hooks = git-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              # ── フォーマット（Nix / TOML / JSON / YAML / shell）──
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
