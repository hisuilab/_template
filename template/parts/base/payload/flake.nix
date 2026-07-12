{
  description = "{{project_name}}";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    { nixpkgs, treefmt-nix, ... }:
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
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.bats
              pkgs.git
              pkgs.gitleaks
              pkgs.just
              pkgs.prek
              pkgs.rumdl
              pkgs.shellcheck
              pkgs.shfmt
              treefmtEval.${system}.config.build.wrapper
            ];

            shellHook = ''
              if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
                prek install --hook-type pre-commit --hook-type commit-msg >/dev/null
              fi
            '';
          };
        }
      );
    };
}
