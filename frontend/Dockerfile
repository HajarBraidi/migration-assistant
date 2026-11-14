# Serveur de développement Vite
FROM node:20-alpine

WORKDIR /app

# 1) Installer les dépendances (mis en cache si package.json ne change pas)
COPY package.json ./
RUN npm install

# 2) Copier le code
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
