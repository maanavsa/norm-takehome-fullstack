'use client';

import HeaderNav from '@/components/HeaderNav';
import LegalQueryForm from '@/components/LegalQueryForm';

export default function Page() {
  return (
    <>
      <HeaderNav signOut={() => {}} />
      <LegalQueryForm />
    </>
  );
}
