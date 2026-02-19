import {getRequestConfig} from 'next-intl/server';

export const locales = ['en', 'es'];
export const defaultLocale = 'es';
 
export default getRequestConfig(async ({locale}) => {
  // Fallback to default if locale is undefined or not in allowed list
  const activeLocale = locale && locales.includes(locale) ? locale : defaultLocale;
  
  return {
    locale: activeLocale,
    messages: (await import(`./messages/${activeLocale}.json`)).default
  };
});
