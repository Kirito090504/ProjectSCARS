import { Button, Card, Container, Group, SimpleGrid, Text, Title } from "@mantine/core";
import { IconChartBar, IconServer, IconShield } from "@tabler/icons-react";
import { motion } from "framer-motion";
import { memo } from "react";

import Carousel from "../ReactBits/Carousel";

const FeatureCard = memo(
    ({ icon: Icon, title, description }: { icon: typeof IconServer; title: string; description: string }) => (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Group mb="md">
                    <Icon size={24} color="var(--mantine-color-blue-6)" />
                    <Title order={4}>{title}</Title>
                </Group>
                <Text size="sm" c="dimmed">
                    {description}
                </Text>
            </Card>
        </motion.div>
    )
);

FeatureCard.displayName = "FeatureCard";

const features = [
    {
        icon: IconServer,
        title: "Asset Management",
        description: "Streamline your school's asset tracking and management with our comprehensive system.",
    },
    {
        icon: IconShield,
        title: "Secure System",
        description: "Enterprise-grade security to protect your institution's sensitive data.",
    },
    {
        icon: IconChartBar,
        title: "Real-time Analytics",
        description: "Make informed decisions with instant access to vital statistics and reports.",
    },
];

export const HomeSection = memo(() => {
    return (
        <Container size="xl" mt={50}>
            {/* Hero Section */}
            <Card shadow="sm" p="xl" radius="md" withBorder mb={50}>
                <Group align="flex-start" gap={50}>
                    <div style={{ flex: 1 }}>
                        <Title mb="md">School Capital Asset Recording System</Title>
                        <Text size="lg" c="dimmed" mb="xl">
                            Transform your school&apos;s asset management with our state-of-the-art digital solution.
                            Track, manage, and generate reports for all your institution&apos;s resources in one place.
                        </Text>
                        <Button
                            component="a"
                            href="/administration/reports"
                            size="md"
                            variant="gradient"
                            gradient={{ from: "blue", to: "cyan" }}
                        >
                            Learn More
                        </Button>
                    </div>
                    <Card
                        w={400}
                        h={300}
                        bg="gray.0"
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                        }}
                    >
                        <IconServer size={100} opacity={0.2} />
                    </Card>
                </Group>
            </Card>

            {/* Features Section */}
            <Title order={2} ta="center" mb="xl">
                Key Features
            </Title>
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg">
                {features.map((feature, index) => (
                    <FeatureCard
                        key={index}
                        icon={feature.icon}
                        title={feature.title}
                        description={feature.description}
                    />
                ))}
            </SimpleGrid>

            <div style={{ height: "600px", position: "relative" }}>
                <Carousel
                    baseWidth={300}
                    autoplay={true}
                    autoplayDelay={3000}
                    pauseOnHover={true}
                    loop={true}
                    round={false}
                />
            </div>
        </Container>
    );
});

HomeSection.displayName = "HomeSection";
