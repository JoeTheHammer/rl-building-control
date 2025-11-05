FROM node:20-alpine

ENV NODE_ENV=production \
    ENV=production \
    TESTBED_PATH=/app \
    TESTBED_IMAGE=myproject/testbed:latest \
    FRONTEND_PORT=5173 \
    BACKEND_PORT=8000

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
