{ ... }:
{
  projectRootFile = "flake.nix";

  programs.nixfmt.enable = true;
  programs.taplo.enable = true;
  programs.prettier = {
    enable = true;
    includes = [
      "*.json"
      "*.ts"
      "*.tsx"
      "*.yaml"
      "*.yml"
    ];
  };

  programs.shellcheck = {
    enable = true;
    includes = [
      "*.sh"
      "*.bash"
      "*.bats"
      "scripts/check-readme"
      "scripts/check-status"
      "scripts/check-encoding"
    ];
  };
  programs.shfmt = {
    enable = true;
    includes = [
      "*.sh"
      "*.bash"
      "*.bats"
      "scripts/check-readme"
      "scripts/check-status"
      "scripts/check-encoding"
    ];
  };
}
