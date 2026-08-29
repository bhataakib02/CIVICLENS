'use client';

import React, { useState, useEffect } from 'react';
import { getNotifications } from '@/lib/api/notifications';
import { Notification } from '@/types/api';
import { realtimeClient } from '@/lib/websocket/realtime-client';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate } from '@/lib/formatting/date';
import { Bell, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export function NotificationList() {
  const { t } = useTranslation();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getNotifications();
      setNotifications(data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch notifications.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();

    // Subscribe to realtime updates
    const unsubscribe = realtimeClient.subscribe((event) => {
      if (event.type === 'document.status_changed' || event.type === 'application.status_changed') {
        fetchNotifs();
      }
    });

    return () => unsubscribe();
  }, []);

  const handleMarkAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">{t.notifications.title}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.notifications.subtitle}</p>
        </div>
        <Button variant="outline" onClick={handleMarkAllRead} disabled={notifications.length === 0}>
          <CheckCircle2 className="w-4 h-4 mr-2 text-emerald-600" />
          {t.notifications.markAllRead}
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      ) : notifications.length === 0 ? (
        <Card className="text-center py-12">
          <Bell className="w-12 h-12 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-500 text-sm">{t.common.noData}</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((notif) => (
            <Card
              key={notif.id}
              className={`p-4 transition-colors border-l-4 ${
                notif.is_read ? 'bg-white border-l-slate-300' : 'bg-blue-50/40 border-l-blue-600'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-xl mt-0.5 ${notif.is_read ? 'bg-slate-100 text-slate-500' : 'bg-blue-100 text-blue-700'}`}>
                    <Bell className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-slate-900 text-sm">{notif.title || `Notification (${notif.category})`}</h4>
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                        {notif.channel}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">{notif.message || `Category update for ${notif.category}`}</p>
                    <span className="text-[11px] text-slate-400 font-mono block mt-1.5">{formatDate(notif.sent_at)}</span>
                  </div>
                </div>

                {notif.application_id && (
                  <Link href={`/applications/${notif.application_id}`}>
                    <Button size="sm" variant="ghost">
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </Link>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
