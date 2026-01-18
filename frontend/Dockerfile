FROM node:16-alpine as build-stage

# 确保使用root用户执行构建操作
USER root

# 设置工作目录并确保权限正确
WORKDIR /app
RUN chmod 777 /app

# 复制依赖文件并安装，使用--unsafe-perm确保root用户可以安装依赖
COPY package*.json ./
RUN npm install --unsafe-perm

# 复制所有文件并确保权限正确
COPY . .
RUN chmod -R 777 /app/node_modules

# 执行构建命令
RUN npm run build

FROM nginx:alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]