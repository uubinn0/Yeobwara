import toast from 'react-hot-toast';

export const showToast = {
  success: (message: string) => {
    toast.success(message, {
      style: {
        background: 'rgb(17, 24, 39)',
        color: '#fff',
        border: '1px solid rgb(55, 65, 81)',
        borderRadius: '0.5rem',
        padding: '1rem',
        whiteSpace: 'pre-line',
        maxWidth: '500px',
        wordBreak: 'break-word'
      }
    });
  },
  error: (message: string) => {
    toast.error(message, {
      style: {
        background: 'rgb(17, 24, 39)',
        color: '#fff',
        border: '1px solid rgb(55, 65, 81)',
        borderRadius: '0.5rem',
        padding: '1rem',
        whiteSpace: 'pre-line',
        maxWidth: '500px',
        wordBreak: 'break-word'
      }
    });
  },
  loading: (message: string) => {
    toast.loading(message, {
      style: {
        background: 'rgb(17, 24, 39)',
        color: '#fff',
        border: '1px solid rgb(55, 65, 81)',
        borderRadius: '0.5rem',
        padding: '1rem',
        whiteSpace: 'pre-line',
        maxWidth: '500px',
        wordBreak: 'break-word'
      }
    });
  },
  dismiss: () => {
    toast.dismiss();
  }
}; 