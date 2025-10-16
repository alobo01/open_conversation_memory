.PHONY: help setup build test lint clean deploy-local stop

# Default target
help:
	@echo "EmoRobCare - Comandos disponibles:"
	@echo "  setup     - Configurar entorno de desarrollo"
	@echo "  build     - Construir todas las imágenes Docker"
	@echo "  test      - Ejecutar todos los tests"
	@echo "  lint      - Ejecutar linting y formateo"
	@echo "  clean     - Limpiar contenedores e imágenes"
	@echo "  deploy-local - Desplegar localmente todos los servicios"
	@echo "  stop      - Detener todos los servicios"
	@echo "  docs      - Generar documentación"

# Setup del entorno
setup:
	@echo "🔧 Configurando entorno de desarrollo..."
	python -m venv venv
	source venv/bin/activate && pip install --upgrade pip
	source venv/bin/activate && pip install ruff black mypy pytest pre-commit
	source venv/bin/activate && pre-commit install
	cd services/frontend && npm install
	@echo "✅ Entorno configurado correctamente"

# Construir imágenes Docker
build:
	@echo "🏗️ Construyendo imágenes Docker..."
	docker build -t emorobcare-api -f services/api/Dockerfile .
	docker build -t emorobcare-asr -f services/asr/Dockerfile .
	docker build -t emorobcare-ui -f services/frontend/Dockerfile .
	docker build -t emorobcare-fuseki -f services/fuseki-job/Dockerfile .
	@echo "✅ Imágenes construidas correctamente"

# Tests
test:
	@echo "🧪 Ejecutando tests..."
	source venv/bin/activate && pytest tests/ -v --cov=services/api
	cd services/frontend && npm test

# Linting y formateo
lint:
	@echo "🔍 Ejecutando linting..."
	source venv/bin/activate && ruff check .
	source venv/bin/activate && black --check .
	source venv/bin/activate && mypy services/
	cd services/frontend && npm run lint

# Formatear código
format:
	@echo "✨ Formateando código..."
	source venv/bin/activate && black .
	source venv/bin/activate && ruff check --fix .
	cd services/frontend && npm run format

# Limpiar
clean:
	@echo "🧹 Limpiando contenedores e imágenes..."
	docker stop $$(docker ps -aq) 2>/dev/null || true
	docker rm $$(docker ps -aq) 2>/dev/null || true
	docker system prune -f

# Despliegue local
deploy-local: build
	@echo "🚀 Desplegando servicios localmente..."
	@echo "Iniciando bases de datos..."
	docker run -d --name mongodb -p 27017:27017 mongo:7
	docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
	docker run -d --name fuseki -p 3030:3030 stain/jena-fuseki
	sleep 5
	@echo "Iniciando servicios de aplicación..."
	docker run -d --name api -p 8000:8000 \
		-e MONGODB_URI=mongodb://host.docker.internal:27017 \
		-e QDRANT_URL=http://host.docker.internal:6333 \
		-e FUSEKI_URL=http://host.docker.internal:3030 \
		emorobcare-api
	docker run -d --name asr -p 8001:8001 \
		emorobcare-asr
	docker run -d --name ui -p 81:80 \
		-e API_URL=http://host.docker.internal:8000 \
		emorobcare-ui
	@echo "✅ Servicios desplegados correctamente"
	@echo "📊 UI disponible en: http://localhost:81"
	@echo "🔌 API disponible en: http://localhost:8000"

# Detener servicios
stop:
	@echo "⏹️ Deteniendo servicios..."
	docker stop mongodb qdrant fuseki api asr ui 2>/dev/null || true
	docker rm mongodb qdrant fuseki api asr ui 2>/dev/null || true
	@echo "✅ Servicios detenidos"

# Verificar estado
status:
	@echo "📊 Estado de los servicios:"
	@echo "Contenedores activos:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo "Servicios web:"
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ API: OK" || echo "❌ API: ERROR"
	@curl -s http://localhost:8001/health > /dev/null && echo "✅ ASR: OK" || echo "❌ ASR: ERROR"
	@curl -s http://localhost:81 > /dev/null && echo "✅ UI: OK" || echo "❌ UI: ERROR"

# Logs
logs:
	docker logs -f api

# Documentación
docs:
	@echo "📚 Generando documentación..."
	mkdir -p docs/api
	curl -s http://localhost:8000/openapi.json | python -m json.tool > docs/api/openapi.json
	@echo "✅ Documentación generada en docs/"

# Desarrollo
dev-api:
	@echo "🔧 Iniciando API en modo desarrollo..."
	cd services/api && source ../../venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-ui:
	@echo "🔧 Iniciando UI en modo desarrollo..."
	cd services/frontend && npm run dev -- --host 0.0.0.0 --port 81

# Tests de integración
test-integration:
	@echo "🔬 Ejecutando tests de integración..."
	source venv/bin/activate && pytest tests/integration/ -v -s

# Tests de rendimiento
test-performance:
	@echo "⚡ Ejecutando tests de rendimiento..."
	source venv/bin/activate && pytest tests/performance/ -v

# Backup de datos
backup:
	@echo "💾 Creando backup de datos..."
	mkdir -p backups
	docker exec mongodb mongodump --out /tmp/backup
	docker cp mongodb:/tmp/backup backups/mongo_$(shell date +%Y%m%d_%H%M%S)
	@echo "✅ Backup completado"

# Instalación completa
install: setup build
	@echo "🎦 Instalación completada"
	@echo "Ejecuta 'make deploy-local' para iniciar los servicios"