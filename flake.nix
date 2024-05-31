{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } {
    systems = import inputs.systems;
    perSystem = { pkgs, lib, ... }: let
      pyVers = map (v: "python${v}") [ "39" "310" "311" "312" "313" ];
    in rec {
      packages = lib.listToAttrs (map
        (python: {
          name = "poetry-plugin-pypi-proxy-${python}";
          value = pkgs.callPackage ./. { python3 = pkgs.${python}; };
        })
        pyVers
      ) // {
        default = packages.poetry-plugin-pypi-proxy-python312;
      };

      devShells.default = let
      in pkgs.mkShell {
        packages = [ pkgs.python312 ] ++ (with pkgs; [
          poetry
          pre-commit
        ]);
      };
    };
  };
}
