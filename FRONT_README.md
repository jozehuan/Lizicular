# Resumen del Prototipo Frontend: Lizicular

Este documento resume la estructura y funcionalidad del prototipo frontend para la aplicación "Lizicular", generado con v0 y construido con Next.js.

## 🚀 Tecnologías Clave

*   **Framework**: [Next.js](https://nextjs.org/) (v16.0.10) - Aplicación React con renderizado del lado del servidor (SSR) o generación de sitios estáticos (SSG).
*   **Lenguaje**: [TypeScript](https://www.typescriptlang.org/) - Para un desarrollo más robusto y escalable.
*   **Componentes UI**: [Radix UI](https://www.radix-ui.com/) (`@radix-ui/*`) - Proporciona componentes UI sin estilos, accesibles y personalizables, permitiendo un alto grado de control sobre el diseño.
*   **Estilos**: [Tailwind CSS](https://tailwindcss.com/) - Enfoque "utility-first" para un estilado rápido y consistente, complementado con `autoprefixer` y `postcss`. Incluye `tailwindcss-animate` para animaciones.
*   **Iconos**: [Lucide React](https://lucide.dev/) - Biblioteca de iconos.
*   **Gestión de Formularios**: [React Hook Form](https://react-hook-form.com/) (`react-hook-form`) y [Zod](https://zod.dev/) (`zod`, `@hookform/resolvers`) - Para una validación de formularios robusta y basada en esquemas.
*   **Gestión de Temas**: [Next Themes](https://github.com/pacocoursey/next-themes) - Para alternar entre temas (ej. modo oscuro/claro).
*   **Visualización de Datos**: [Recharts](https://recharts.org/) - Biblioteca de gráficos, sugiriendo funcionalidades de tablero o reportes.
*   **Autenticación (Frontend)**: [JOSE](https://github.com/panva/jose) (`jose`) - Podría utilizarse para la manipulación o verificación de tokens JWT en el frontend.
*   **Analíticas**: [Vercel Analytics](https://vercel.com/analytics) - Integración para el seguimiento del uso de la aplicación.

## 📂 Estructura del Proyecto Frontend

La estructura del directorio `app` en Next.js App Router sugiere una organización por funcionalidades:

*   `/app`: Contiene las rutas principales de la aplicación.
    *   `globals.css`: Estilos globales de la aplicación.
    *   `layout.tsx`: Define el layout raíz, incluyendo el `AuthProvider` (para la gestión global de la autenticación) y la configuración de metadatos/fuentes.
    *   `page.tsx`: La página de inicio o "landing page" que introduce la plataforma Lizicular.
    *   `/api`: Es probable que contenga rutas API de Next.js para interactuar con el backend o servicios externos.
    *   `/auth`: Se espera que contenga páginas y/o componentes relacionados con el proceso de autenticación (login, registro).
    *   `/dashboard`: Probablemente contenga las páginas y componentes del panel de control principal de la aplicación.
    *   `/space`: Podría estar relacionado con la gestión de "espacios de trabajo" (workspaces) o módulos específicos dentro de la aplicación.
*   `/components`: Componentes reutilizables de la UI (ej. botones, tarjetas).
*   `/hooks`: React Hooks personalizados para lógica reutilizable.
*   `/lib`: Utilidades y librerías auxiliares (ej. `auth-context.ts` para el proveedor de autenticación).
*   `/public`: Archivos estáticos como iconos.
*   `/styles`: Configuración de estilos más allá de Tailwind (si aplica).

## 💡 Funcionalidad Principal (según la Landing Page)

La página de inicio (`app/page.tsx`) funciona como una introducción a la plataforma Lizicular, destacando sus capacidades:

*   **Gestión de Licitaciones y Automatización**: Propuesta de valor central de la plataforma.
*   **Características Clave Anunciadas**:
    *   **Document Management**: Carga y organización de documentos (PDF, etc.).
    *   **Team Collaboration**: Invitación de colaboradores y trabajo en equipo en licitaciones.
    *   **Analysis & Insights**: Análisis automatizado de documentos de licitación.
    *   **AI-Powered Automation**: Extracción de información clave y generación de resúmenes con IA.
*   **Llamadas a la Acción (CTAs)**: Botones para "Sign In", "Get Started", "Start Free Trial" (todos dirigen a `/auth`) y "View Demo" (dirige a `/dashboard`).

## ⚙️ Integración con el Backend (Hipótesis)

Basado en la estructura y las funcionalidades inferidas:

*   El frontend interactuará con los endpoints de autenticación del backend (ej. `/auth/signup`, `/auth/login`) para gestionar el acceso de usuarios.
*   El `AuthProvider` en `layout.tsx` probablemente maneja el estado de autenticación a nivel global y utiliza los tokens JWT obtenidos del backend.
*   La sección `/dashboard` y `/space` interactuarán con los endpoints del backend para la gestión de licitaciones y workspaces respectivamente.

En resumen, el prototipo frontend es una base sólida para una aplicación de gestión de licitaciones, con una arquitectura moderna, un fuerte enfoque en la experiencia de usuario y la preparación para interactuar con el backend para la gestión de datos y autenticación.
