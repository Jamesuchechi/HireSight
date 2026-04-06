import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import TrustCloud from "@/components/TrustCloud";
import FeatureGrid from "@/components/FeatureGrid";
import ComparisonSection from "@/components/ComparisonSection";
import ScreeningPreview from "@/components/ScreeningPreview";
import Testimonials from "@/components/Testimonials";
import Pricing from "@/components/Pricing";
import FAQ from "@/components/FAQ";
import RoleSelection from "@/components/RoleSelection";
import Footer from "@/components/Footer";
import CustomCursor from "@/components/CustomCursor";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-white selection:bg-primary/20 selection:text-primary overflow-x-hidden">
      {/* Premium Custom Cursor */}
      <CustomCursor />

      {/* Navigation */}
      <Navbar />

      <main className="flex-grow">
        {/* Futuristic Hero with Parallax & Typewriter */}
        <Hero />

        {/* Industry Trust Cloud */}
        <TrustCloud />

        {/* Intelligent Features Grid */}
        <FeatureGrid />

        {/* AI Match Benchmarking */}
        <ComparisonSection />

        {/* Visual Engine Demo */}
        <ScreeningPreview />

        {/* Social Proof & Success Stories */}
        <Testimonials />

        {/* Value-Based Pricing */}
        <Pricing />

        {/* Knowledge & Support */}
        <FAQ />

        {/* Final Conversion Section */}
        <RoleSelection />
      </main>

      {/* Flagship Footer */}
      <Footer />
    </div>
  );
}
