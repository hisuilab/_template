{ ... }:
{
  projectRootFile = "flake.nix";
  imports = [ ./treefmt-base.nix ];
  programs.gofmt.enable = true;
}
