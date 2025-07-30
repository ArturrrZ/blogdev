# Dockerfile
FROM node:20-slim

WORKDIR /react

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build