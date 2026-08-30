import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from '../../components/ui/status-badge';

describe('StatusBadge Component', () => {
  it('renders eligible status badge correctly with accessible description', () => {
    render(<StatusBadge status="eligible" />);
    const badge = screen.getByText('✓ Eligible');
    expect(badge).toBeInTheDocument();
  });

  it('renders verified document status badge', () => {
    render(<StatusBadge status="verified" />);
    const badge = screen.getByText('✓ Verified');
    expect(badge).toBeInTheDocument();
  });

  it('renders application action_required status badge', () => {
    render(<StatusBadge status="action_required" />);
    const badge = screen.getByText('⚠ Action Required');
    expect(badge).toBeInTheDocument();
  });
});
