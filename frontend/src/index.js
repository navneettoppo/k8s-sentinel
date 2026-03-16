import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import App from './App';

const theme = extendTheme({
  config: { initialColorMode: 'dark', useSystemColorMode: false },
  colors: {
    brand: { 50: '#e6f2ff', 100: '#b3d9ff', 500: '#0073e6', 600: '#005bb3', 900: '#002a4d' }
  },
  styles: {
    global: { body: { bg: 'gray.900', color: 'white' } }
  },
  components: {
    Card: { baseStyle: { container: { bg: 'gray.800', borderColor: 'gray.700' } } }
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </React.StrictMode>
);
