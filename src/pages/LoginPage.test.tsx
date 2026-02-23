import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import LoginPage from './LoginPage';

describe('LoginPage', () => {
  it('toggles password visibility when the eye icon is clicked', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;
    const toggleButton = screen.getByLabelText('Show password');

    // Initial state: password type
    expect(passwordInput.type).toBe('password');

    // Click to show
    fireEvent.click(toggleButton);
    expect(passwordInput.type).toBe('text');
    expect(screen.getByLabelText('Hide password')).toBeInTheDocument();

    // Click to hide again
    fireEvent.click(screen.getByLabelText('Hide password'));
    expect(passwordInput.type).toBe('password');
    expect(screen.getByLabelText('Show password')).toBeInTheDocument();
  });

  it('contains an email field and a sign-in button', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });
});
