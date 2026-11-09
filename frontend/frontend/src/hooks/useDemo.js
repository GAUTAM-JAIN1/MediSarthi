import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../config';

export function useDemo() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isHidden, setIsHidden] = useState(false);
  const navigate = useNavigate();

  const startDemo = async () => {
    setLoading(true);
    setMessage('');

    try {
      const res = await fetch(`${API_BASE}/demo/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('ms_token', data.access_token);
        localStorage.setItem('ms_user_id', data.user_id);
        localStorage.setItem('ms_user_name', data.name);
        navigate('/health-info');
        return;
      }

      if (res.status === 404 || res.status === 403) {
        setMessage('Demo is not enabled on this server.');
        setIsHidden(true);
        return;
      }

      if (res.status === 429) {
        setMessage('Too many demo sessions, try again in a minute.');
        return;
      }

      setMessage('Demo could not start. Try again.');
    } catch {
      setMessage('Demo could not start. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return {
    startDemo,
    loading,
    message,
    isHidden,
  };
}
