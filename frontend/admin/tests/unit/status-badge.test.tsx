import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from '@/components/ui/status-badge';

describe('Admin StatusBadge Component', () => {
  it('renders status label formatted correctly', () => {
    render(<StatusBadge status="under_review" />);
    expect(screen.getByText('Under Review')).toBeInTheDocument();
  });

  it('applies success styling for approved status', () => {
    const { container } = render(<StatusBadge status="approved" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('text-emerald-400');
  });

  it('applies alert styling for action_required status', () => {
    const { container } = render(<StatusBadge status="action_required" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('text-amber-400');
  });

  it('applies danger styling for rejected status', () => {
    const { container } = render(<StatusBadge status="rejected" />);
    const badge = container.querySelector('span');
    expect(badge?.className).toContain('text-red-400');
  });
});
