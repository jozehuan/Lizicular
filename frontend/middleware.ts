import createMiddleware from 'next-intl/middleware';
import { locales, defaultLocale } from './i18n';

export default createMiddleware({
  // A list of all locales that are supported
  locales: ['en', 'es'],
 
  // Used when no locale matches
  defaultLocale: 'es',
  localePrefix: 'always' // Asegura que el locale esté siempre en la URL
});
 
export const config = {
  // Matcher que ignora archivos internos y estáticos
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
};
