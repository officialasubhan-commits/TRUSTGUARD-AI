import React from 'react';
import { Link } from 'react-router-dom';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex-1 flex items-center justify-center py-20">
      <Container size="sm">
        <Card pixelFrame className="text-center space-y-6">
          <div className="space-y-2">
            <span className="text-4xl font-mono font-bold text-[#F5F5F5] block">404</span>
            <h1 className="text-xl font-light text-[#F5F5F5]">RESOURCE UNRESOLVABLE</h1>
            <p className="text-xs font-mono text-[#A1A1A1]">
              THE REQUESTED ROUTE DOES NOT EXIST OR HAS DISSOLVED.
            </p>
          </div>

          <div>
            <Link to="/">
              <Button>RETURN TO BASE</Button>
            </Link>
          </div>
        </Card>
      </Container>
    </div>
  );
};

