FROM postgres:15-alpine

# Install additional tools
RUN apk add --no-cache \
    bash \
    curl \
    postgresql-client \
    tzdata \
    && rm -rf /var/cache/apk/*

# Set timezone BEFORE installing tzdata (more efficient)
ENV TZ=Africa/Algiers
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/
COPY backup.sh /usr/local/bin/backup.sh

# Make backup script executable
RUN chmod +x /usr/local/bin/backup.sh

# Create backup directory
RUN mkdir -p /backups && chown postgres:postgres /backups

# Health check - NOTE: This won't work here because environment variables aren't set yet
# Move this logic to init.sql or a separate script

# Expose port
EXPOSE 5432

# Run the original entrypoint (important!)
CMD ["postgres"]