# Workflow Service - Step Function Manual

## ⚠️ Importante

El **Step Function NO se despliega automáticamente** con `serverless deploy`.

Solo se crean las **tablas DynamoDB**.

## 📋 Cómo crear el Step Function manualmente

### 1. Ve a AWS Console → Step Functions

### 2. Create state machine
- Click en **"Create state machine"**
- Selecciona **"Write your workflow in code"**
- Selecciona **"Standard"** type

### 3. Copia el JSON
- Abre el archivo `step-function.json` en este directorio
- **Copia TODO el contenido**
- Pega en el editor de AWS Console

### 4. Configuración
- **Name:** `BurgerFlow-dev` (o el stage que uses)
- **Execution role:** Selecciona `LabRole`
- **Logging:** Opcional (recomendado: ALL para debugging)

### 5. Create

¡Listo! El Step Function quedará configurado con las Lambdas:
- ✅ `burger-kitchen-dev-validateStock`
- ✅ `burger-auth-dev-registerToken`

## 📝 Notas

- Los ARNs de las Lambdas ya están hardcodeados en `step-function.json`
- Si cambias de región/cuenta, actualiza los ARNs en el JSON
- El Step Function tiene 18 estados incluyendo reintentos y timeouts
