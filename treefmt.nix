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

  # scripts/ 配下のshebangのみで拡張子が無いスクリプトは、既定のincludesに明示的に追加します。
  programs.shellcheck = {
    enable = true;
    includes = [
      "*.sh"
      "*.bash"
      "*.bats"
      "scripts/precommit"
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
      "scripts/precommit"
      "scripts/check-readme"
      "scripts/check-status"
      "scripts/check-encoding"
    ];
  };
}
