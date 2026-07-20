{ ... }:
{
  projectRootFile = "flake.nix";
  imports = [ ./treefmt-base.nix ];
  programs.rustfmt.enable = true;
}
