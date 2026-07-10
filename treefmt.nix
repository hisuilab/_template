{ ... }:
{
  projectRootFile = "flake.nix";

  programs.nixfmt.enable = true;
  programs.taplo.enable = true;
  programs.prettier = {
    enable = true;
    includes = [
      "*.json"
      "*.yaml"
      "*.yml"
    ];
  };

  # scripts/precommit, scripts/check-readme はshebangのみで拡張子が無いため、既定のincludesに明示的に追加します。
  programs.shellcheck = {
    enable = true;
    includes = [
      "*.sh"
      "*.bash"
      "*.bats"
      "scripts/precommit"
      "scripts/check-readme"
    ];
  };
  programs.shfmt = {
    enable = true;
    includes = [
      "*.sh"
      "*.bash"
      "*.bats"
      "scripts/precommit"
      "scripts/check-readme"
    ];
  };
}
