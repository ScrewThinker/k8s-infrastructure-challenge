FROM node:22-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

RUN touch /run/nginx.pid && \
    chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /etc/nginx/conf.d /run/nginx.pid

USER nginx
EXPOSE 8080
