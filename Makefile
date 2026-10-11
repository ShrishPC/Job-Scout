.PHONY: test bench up down

up:
	docker compose up -d

down:
	docker compose down

test:
	docker compose exec -T backend python -m pytest /app/tests -v --cov=app --cov-report=term-missing

bench:
	bash scripts/run_all_benchmarks.sh
