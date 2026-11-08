import React from 'react';
import { Check, X } from 'lucide-react';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export const AdminPage: React.FC = () => {
  return (
    <div className="flex-1 py-12 md:py-20">
      <Container size="lg">
        <div className="space-y-8">
          <div className="space-y-1">
            <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-[#F5F5F5]">
              Administrative Moderation Desk
            </h1>
            <p className="text-xs sm:text-sm text-[#A1A1A1] font-mono">
              COMMUNITY THREAT REPORT REVIEW & VERIFICATION
            </p>
          </div>

          <Card pixelFrame className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#292929] pb-3 text-xs font-mono text-[#666666]">
              <span>PENDING MODERATION QUEUE (2 ITEMS)</span>
              <span>ROLE: ADMIN CONFIRMED</span>
            </div>

            <div className="space-y-3">
              <div className="p-4 bg-[#101010] border border-[#292929] flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2 text-xs font-mono">
                    <span className="px-2 py-0.5 bg-[#F5F5F5] text-[#080808] font-semibold">
                      PENDING REVIEW
                    </span>
                    <span className="text-[#666666]">REPORTED 2 HOURS AGO</span>
                  </div>
                  <p className="text-sm font-mono text-[#F5F5F5]">https://credential-steal.biz</p>
                  <p className="text-xs text-[#A1A1A1]">
                    User reported: &quot;Targeting internal HR portal with spear phishing form.&quot;
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <Button size="sm" variant="outline" leftIcon={<Check className="w-3.5 h-3.5" />}>
                    APPROVE
                  </Button>
                  <Button size="sm" variant="danger" leftIcon={<X className="w-3.5 h-3.5" />}>
                    REJECT
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </Container>
    </div>
  );
};

