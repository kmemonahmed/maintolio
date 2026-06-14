import { WorkOrderDetailScreen } from "@/components/screens/work-order-detail";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <WorkOrderDetailScreen id={id} />;
}

