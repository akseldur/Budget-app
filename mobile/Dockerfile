FROM node:22-slim AS build
WORKDIR /app
ARG EXPO_PUBLIC_API_URL
ARG EXPO_PUBLIC_API_KEY
ENV EXPO_PUBLIC_API_URL=$EXPO_PUBLIC_API_URL
ENV EXPO_PUBLIC_API_KEY=$EXPO_PUBLIC_API_KEY
COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npx expo export --platform web

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY Caddyfile.web /etc/caddy/Caddyfile
