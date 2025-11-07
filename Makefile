.PHONY: all clean run test

all:
	@echo "Python project — nothing to build. Use 'make run BIN=programs/sample.bin' or 'make step BIN=programs/sample.bin'."

run:
	@python3 -m cpu.main $(BIN)

step:
	@python3 -m cpu.main --step $(BIN)

test:
	@python3 -m pytest -q

clean:
	@rm -rf __pycache__ cpu/__pycache__ .pytest_cache *.pyc *.pyo **/*.pyc **/__pycache__
