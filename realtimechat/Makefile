.PHONY: help install test test-backend test-frontend test-coverage lint clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install all dependencies
	cd realtimechat && pip install -r requirements-dev.txt
	cd frontend && npm install

test: test-backend test-frontend  ## Run all tests

test-backend:  ## Run backend tests
	cd realtimechat && source venv/bin/activate && python -m pytest tests/ -v

test-frontend:  ## Run frontend tests
	cd frontend && npm test

test-coverage:  ## Run tests with coverage
	cd realtimechat && source venv/bin/activate && python -m pytest tests/ -v --cov --cov-report=html
	cd frontend && npm run test:coverage

lint:  ## Run linting
	cd frontend && npx vue-tsc --noEmit

clean:  ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf realtimechat/.pytest_cache realtimechat/htmlcov realtimechat/.coverage
	rm -rf frontend/node_modules/.vite
