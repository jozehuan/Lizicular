-- Script de inicialización de la base de datos Lizicular
-- Generado para PostgreSQL 15

-- 1. Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Crear tipos ENUM
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'workspacerole') THEN
        CREATE TYPE workspacerole AS ENUM ('OWNER', 'ADMIN', 'EDITOR', 'VIEWER');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'auditcategory') THEN
        CREATE TYPE auditcategory AS ENUM ('AUTH', 'WORKSPACE', 'TENDER', 'DOCUMENT', 'SYSTEM', 'N8N');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'auditaction') THEN
        CREATE TYPE auditaction AS ENUM (
            'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'PASSWORD_CHANGE', 'OAUTH_LOGIN', 'USER_VIEW',
            'WORKSPACE_CREATE', 'WORKSPACE_UPDATE', 'WORKSPACE_DELETE', 'MEMBER_ADD', 'MEMBER_REMOVE', 'ROLE_CHANGE',
            'TENDER_CREATE', 'TENDER_UPDATE', 'TENDER_DELETE', 'TENDER_VIEW', 'TENDER_ANALYZE',
            'DOCUMENT_UPLOAD', 'DOCUMENT_DELETE', 'DOCUMENT_EXTRACT',
            'SYSTEM_ERROR', 'SYSTEM_BACKUP',
            'WORKFLOW_START', 'WORKFLOW_COMPLETE', 'WORKFLOW_ERROR'
        );
    END IF;
END $$;

-- 3. Tabla de Usuarios
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    profile_picture TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_email_active ON users (email, is_active);
CREATE INDEX IF NOT EXISTS ix_users_oauth_provider_id ON users (oauth_provider, oauth_id);

-- 4. Tabla de Workspaces
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_workspaces_owner_active ON workspaces (owner_id, is_active);

-- 5. Tabla de Miembros de Workspace (RBAC)
CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role workspacerole NOT NULL DEFAULT 'VIEWER',
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, user_id)
);

CREATE INDEX IF NOT EXISTS ix_workspace_members_user_id ON workspace_members (user_id);
CREATE INDEX IF NOT EXISTS ix_workspace_members_workspace_id ON workspace_members (workspace_id);

-- 6. Tabla de Logs de Auditoría
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    category auditcategory NOT NULL,
    action auditaction NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    workspace_id UUID,
    payload JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices de Auditoría
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_category ON audit_logs (category);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);
CREATE INDEX IF NOT EXISTS ix_audit_user_created ON audit_logs (user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_audit_category_action ON audit_logs (category, action, created_at);
CREATE INDEX IF NOT EXISTS ix_audit_workspace_created ON audit_logs (workspace_id, created_at);
CREATE INDEX IF NOT EXISTS ix_audit_resource ON audit_logs (resource_type, resource_id);
CREATE INDEX IF NOT EXISTS ix_audit_payload ON audit_logs USING GIN (payload);
CREATE INDEX IF NOT EXISTS ix_audit_failures ON audit_logs (success, created_at) WHERE success = FALSE;

-- 7. Tabla de Automatismos
CREATE TABLE IF NOT EXISTS autos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

-- Insertar automatismo por defecto
-- Nota: La columna owner_id es NOT NULL, por lo que necesitamos un usuario existente.
-- Insertamos un usuario por defecto si no existe.
INSERT INTO users (id, email, hashed_password, full_name, is_active)
VALUES ('00000000-0000-0000-0000-000000000001', 'lizicular@nazaries.com', 'passwordpassword', 'LIZICULAR OWNER', TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO autos (id, url, name, description, owner_id)
VALUES ('2cf9e384-b633-5c8c-9488-2f47b6796791', 'https://n8n.staging.nazaries.cloud/webhook-test/7dda4f32-7721-405b-aa6d-8e84ded163ce', 'Ticketing Tender Automation', 'This is a default automation for testing purposes.', '00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;