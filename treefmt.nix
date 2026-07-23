{ ... }:
{
  projectRootFile = "flake.nix";

  programs.nixfmt = {
    enable = true;
    # template/parts/payload/ 配下の *.nix ファイルはジェネレータのテンプレートであり、
    # {{lang_packages}} のようなプレースホルダを含むため nixfmt の対象から除外します。
    excludes = [ "template/parts/**/payload/*.nix" ];
  };
  programs.taplo.enable = true;
  programs.prettier = {
    enable = true;
    includes = [
      "*.json"
      "*.yaml"
      "*.yml"
    ];
  };

  programs.ruff-format.enable = true;

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
      "scripts/github-setup-rules"
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
      "scripts/github-setup-rules"
    ];
  };
}
