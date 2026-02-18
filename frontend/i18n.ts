import {getRequestConfig} from 'next-intl/server';

export const locales = ['en', 'es'];
export const defaultLocale = 'es';
 
export default getRequestConfig(async ({locale}) => {
  // Fallback si locale no está definido por alguna razón
  const activeLocale = locale || defaultLocale;
  
  return {
    locale: activeLocale,
    messages: (await import(`./messages/${activeLocale}.json`)).default
  };
});
