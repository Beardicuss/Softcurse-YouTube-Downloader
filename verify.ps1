$ErrorActionPreference = "Stop"

Write-Host "[1/3] Compiling Python sources"
python -m compileall -q -x "(build|dist)" .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/3] Running Ruff correctness checks"
python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/3] Running tests with coverage"
python -m coverage erase
python -m coverage run -m unittest discover -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m coverage report
exit $LASTEXITCODE

