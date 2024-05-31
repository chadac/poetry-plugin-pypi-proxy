{
  lib,
  python3,
}:
python3.pkgs.buildPythonPackage {
  pname = "poetry-plugin-pypi-proxy";
  version = "0.1.3";

  src = lib.cleanSource ./.;
  format = "pyproject";

  nativeBuildInputs = with python3.pkgs; [
    poetry-core
  ];

  propagatedBuildInputs = with python3.pkgs; [
  ];

  checkInputs = with python3.pkgs; [
    pytest
    pytest-mock
    wheel
    pytest-httpserver
    mypy
    types-setuptools
  ];
}
