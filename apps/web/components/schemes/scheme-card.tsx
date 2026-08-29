import React from 'react';
import Link from 'next/link';
import { SchemeSummary } from '@/types/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useTranslation } from '@/lib/i18n';
import { Building2, ArrowRight, Shield } from 'lucide-react';

interface SchemeCardProps {
  scheme: SchemeSummary;
}

export function SchemeCard({ scheme }: SchemeCardProps) {
  const { t } = useTranslation();

  return (
    <Card className="flex flex-col justify-between hover:border-blue-300 transition-all">
      <div>
        <CardHeader className="flex items-start justify-between pb-2">
          <div>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 uppercase tracking-wide mb-2">
              <Building2 className="w-3 h-3" />
              {scheme.scope === 'central' ? t.schemes.central : t.schemes.state}
            </span>
            <CardTitle className="text-base font-bold text-slate-900 line-clamp-2">
              {scheme.canonical_name}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-slate-500 line-clamp-3 mb-4 leading-relaxed">
            {scheme.benefits_summary}
          </p>
          <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            <span>Category: <strong className="text-slate-700 capitalize">{scheme.category}</strong></span>
          </div>
        </CardContent>
      </div>

      <div className="pt-4 border-t border-slate-100 flex items-center justify-between mt-4">
        <Link href={`/schemes/${scheme.id}`} className="w-full">
          <Button variant="outline" className="w-full justify-between text-xs font-semibold text-blue-700 border-blue-200 hover:bg-blue-50">
            <span>{t.common.viewDetails}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </Link>
      </div>
    </Card>
  );
}
