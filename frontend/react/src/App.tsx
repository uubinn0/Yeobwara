import { BrowserRouter } from "react-router-dom";
import Router from "./router";
import { Toaster } from "react-hot-toast";

function App() {
  return (
    <>
      <BrowserRouter>
        <Router />
        <Toaster
          position="top-center"
          reverseOrder={false}
          toastOptions={{
            className: '',
            style: {
              background: 'rgb(17, 24, 39)',
              color: '#fff',
              border: '1px solid rgb(55, 65, 81)',
              borderRadius: '0.5rem',
              padding: '1rem',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
            },
            success: {
              iconTheme: {
                primary: '#10B981',
                secondary: '#fff',
              },
              style: {
                background: 'rgb(17, 24, 39)',
                color: '#fff',
                border: '1px solid rgb(55, 65, 81)',
                borderRadius: '0.5rem',
                padding: '1rem',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
              },
            },
            error: {
              iconTheme: {
                primary: '#EF4444',
                secondary: '#fff',
              },
              style: {
                background: 'rgb(17, 24, 39)',
                color: '#fff',
                border: '1px solid rgb(55, 65, 81)',
                borderRadius: '0.5rem',
                padding: '1rem',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
              },
            },
            duration: 3000,
          }}
        />
      </BrowserRouter>
    </>
  );
}

export default App;
