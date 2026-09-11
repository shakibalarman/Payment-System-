FROM node:20-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install || npm install --legacy-peer-deps
COPY frontend/ .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
