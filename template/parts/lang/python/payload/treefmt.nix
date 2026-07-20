{ ... }:
{
  projectRootFile = "flake.nix";
  imports = [ ./treefmt-base.nix ];
  programs.ruff.enable = true;
}
