FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=development \
    VITE_BACKEND_URL=http://backend \


COPY package.json package-lock.json ./

RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
