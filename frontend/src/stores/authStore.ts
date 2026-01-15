/**
 * NeurOS 2.0 Auth Store (Zustand)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, UserLogin, UserCreate } from '../lib/types';
import { authApi } from '../lib/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: UserLogin) => Promise<boolean>;
  register: (data: UserCreate) => Promise<boolean>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.login(credentials);
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
          return true;
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({ error: message, isLoading: false });
          return false;
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register(data);
          // Auto-login after registration
          return get().login({ email: data.email, password: data.password });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Registration failed';
          set({ error: message, isLoading: false });
          return false;
        }
      },

      logout: () => {
        authApi.logout();
        set({ user: null, isAuthenticated: false });
      },

      fetchUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        set({ isLoading: true });
        try {
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ isAuthenticated: state.isAuthenticated }),
    }
  )
);
