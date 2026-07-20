{ ... }:
{
  projectRootFile = "flake.nix";
  imports = [ ./treefmt-base.nix ];

  programs.biome = {
    enable = true;
    includes = [
      "*.ts"
      "*.tsx"
    ];
  };
}
