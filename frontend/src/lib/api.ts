export const getApiHost = (): string => {
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://backend:8001';
  }
  
  // Docker internal container networking alias support
  if (window.location.hostname === 'frontend') {
    return `${window.location.protocol}//backend:8001`;
  }
  
  return process.env.NEXT_PUBLIC_API_URL || `${window.location.protocol}//${window.location.hostname}:8001`;
};
