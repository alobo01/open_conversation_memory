#!/usr/bin/env python3
"""
Comprehensive test script for the ASR service
Tests all three tiers and various scenarios
"""

import asyncio
import aiohttp
import json
import time
import io
import wave
import numpy as np
from typing import Dict, Any, List

# Test configuration
ASR_BASE_URL = "http://localhost:8001"
TEST_AUDIO_FILE = "test_audio.wav"  # You'll need to provide this

class ASRTester:
    def __init__(self, base_url: str = ASR_BASE_URL):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> Dict[str, Any]:
        """Test the health check endpoint"""
        print("🔍 Testing health check endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                print(f"✅ Health check passed: {data['status']}")
                return {"success": True, "data": data}
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {"success": False, "error": str(e)}

    async def test_service_status(self) -> Dict[str, Any]:
        """Test the detailed service status endpoint"""
        print("📊 Testing service status endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/status") as response:
                data = await response.json()
                print(f"✅ Service status retrieved successfully")
                print(f"   Available models: {list(data['models']['models'].keys())}")
                return {"success": True, "data": data}
        except Exception as e:
            print(f"❌ Service status check failed: {e}")
            return {"success": False, "error": str(e)}

    def generate_test_audio(self, duration: float = 3.0, sample_rate: int = 16000) -> bytes:
        """Generate a simple test audio file with sine wave"""
        print(f"🎵 Generating test audio ({duration}s)...")

        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A4 note
        audio = 0.3 * np.sin(2 * np.pi * frequency * t)

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        buffer.seek(0)
        return buffer.read()

    async def test_transcription_tier(self, tier: str, audio_data: bytes) -> Dict[str, Any]:
        """Test transcription for a specific tier"""
        print(f"🎙️  Testing {tier} tier transcription...")

        data = aiohttp.FormData()
        data.add_field('audio', audio_data,
                      filename='test.wav',
                      content_type='audio/wav')
        data.add_field('tier', tier)

        start_time = time.time()
        try:
            async with self.session.post(f"{self.base_url}/transcribe", data=data) as response:
                result_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    print(f"✅ {tier} tier transcription successful:")
                    print(f"   Text: {data['text']}")
                    print(f"   Language: {data['language']}")
                    print(f"   Confidence: {data['confidence']:.3f}")
                    print(f"   Processing time: {result_time:.3f}s")
                    return {"success": True, "data": data, "total_time": result_time}
                else:
                    error_text = await response.text()
                    print(f"❌ {tier} tier transcription failed: {response.status} - {error_text}")
                    return {"success": False, "error": error_text, "status": response.status}
        except Exception as e:
            print(f"❌ {tier} tier transcription error: {e}")
            return {"success": False, "error": str(e)}

    async def test_all_tiers(self) -> Dict[str, Any]:
        """Test all three transcription tiers"""
        print("\n🧪 Testing all transcription tiers...")

        # Generate test audio
        audio_data = self.generate_test_audio(3.0)

        tiers = ["fast", "balanced", "accurate"]
        results = {}

        for tier in tiers:
            result = await self.test_transcription_tier(tier, audio_data)
            results[tier] = result

            # Brief pause between requests
            await asyncio.sleep(0.5)

        return results

    async def test_benchmark(self, tier: str = "balanced", iterations: int = 3) -> Dict[str, Any]:
        """Test the benchmark endpoint"""
        print(f"⚡ Running benchmark for {tier} tier ({iterations} iterations)...")

        audio_data = self.generate_test_audio(2.0)

        data = aiohttp.FormData()
        data.add_field('audio', audio_data,
                      filename='test.wav',
                      content_type='audio/wav')
        data.add_field('tier', tier)
        data.add_field('iterations', str(iterations))

        try:
            async with self.session.post(f"{self.base_url}/benchmark", data=data) as response:
                if response.status == 200:
                    benchmark_data = await response.json()
                    results = benchmark_data['benchmark_results']

                    print(f"✅ Benchmark completed for {tier}:")
                    print(f"   Average processing time: {results['processing_time']['average']:.3f}s")
                    print(f"   Min/Max time: {results['processing_time']['minimum']:.3f}s / {results['processing_time']['maximum']:.3f}s")
                    print(f"   Consistency: {results['consistency']:.3f}")

                    return {"success": True, "data": benchmark_data}
                else:
                    error_text = await response.text()
                    print(f"❌ Benchmark failed: {response.status} - {error_text}")
                    return {"success": False, "error": error_text}
        except Exception as e:
            print(f"❌ Benchmark error: {e}")
            return {"success": False, "error": str(e)}

    async def test_error_handling(self) -> Dict[str, Any]:
        """Test various error scenarios"""
        print("\n🚨 Testing error handling...")

        error_tests = [
            {
                "name": "Empty audio file",
                "audio": b"",
                "expected_status": 400
            },
            {
                "name": "Non-audio file",
                "audio": b"This is not audio data",
                "content_type": "text/plain",
                "expected_status": 400
            },
            {
                "name": "Invalid tier",
                "audio": self.generate_test_audio(1.0),
                "tier": "invalid_tier",
                "expected_status": 200  # Should fall back to balanced
            }
        ]

        results = {}

        for test in error_tests:
            print(f"   Testing {test['name']}...")

            data = aiohttp.FormData()
            audio_field = data.add_field('audio', test['audio'],
                                       filename='test.wav',
                                       content_type=test.get('content_type', 'audio/wav'))

            if 'tier' in test:
                data.add_field('tier', test['tier'])

            try:
                async with self.session.post(f"{self.base_url}/transcribe", data=data) as response:
                    if response.status == test['expected_status']:
                        print(f"      ✅ Expected status {response.status}")
                        results[test['name']] = {"success": True, "status": response.status}
                    else:
                        response_text = await response.text()
                        print(f"      ❌ Unexpected status {response.status}, expected {test['expected_status']}")
                        results[test['name']] = {"success": False, "status": response.status, "response": response_text}
            except Exception as e:
                print(f"      ❌ Error: {e}")
                results[test['name']] = {"success": False, "error": str(e)}

        return results

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🚀 Starting comprehensive ASR service tests...\n")

        all_results = {
            "timestamp": time.time(),
            "tests": {}
        }

        # Basic connectivity tests
        all_results["tests"]["health_check"] = await self.test_health_check()
        all_results["tests"]["service_status"] = await self.test_service_status()

        # Transcription tests
        all_results["tests"]["all_tiers"] = await self.test_all_tiers()

        # Performance tests
        all_results["tests"]["benchmark_balanced"] = await self.test_benchmark("balanced", 3)
        all_results["tests"]["benchmark_fast"] = await self.test_benchmark("fast", 3)

        # Error handling tests
        all_results["tests"]["error_handling"] = await self.test_error_handling()

        # Get final stats
        try:
            async with self.session.get(f"{self.base_url}/stats") as response:
                if response.status == 200:
                    all_results["final_stats"] = await response.json()
        except Exception as e:
            print(f"⚠️  Could not retrieve final stats: {e}")

        return all_results

    def print_summary(self, results: Dict[str, Any]):
        """Print a summary of test results"""
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)

        total_tests = 0
        passed_tests = 0

        for test_name, test_result in results["tests"].items():
            if isinstance(test_result, dict):
                if "success" in test_result:
                    total_tests += 1
                    if test_result["success"]:
                        passed_tests += 1
                        print(f"✅ {test_name}: PASSED")
                    else:
                        print(f"❌ {test_name}: FAILED")
                elif isinstance(test_result, dict) and test_name == "all_tiers":
                    # Handle tier results
                    for tier, tier_result in test_result.items():
                        total_tests += 1
                        if tier_result.get("success", False):
                            passed_tests += 1
                            print(f"✅ {test_name}.{tier}: PASSED")
                        else:
                            print(f"❌ {test_name}.{tier}: FAILED")
                elif isinstance(test_result, dict) and test_name == "error_handling":
                    # Handle error test results
                    for error_name, error_result in test_result.items():
                        total_tests += 1
                        if error_result.get("success", False):
                            passed_tests += 1
                            print(f"✅ {test_name}.{error_name}: PASSED")
                        else:
                            print(f"❌ {test_name}.{error_name}: FAILED")

        print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")

        if "final_stats" in results:
            stats = results["final_stats"]
            print(f"\n📈 Service Statistics:")
            print(f"   Total transcriptions: {stats.get('total_transcriptions', 0)}")
            print(f"   Average processing time: {stats.get('avg_processing_time', 0):.3f}s")
            print(f"   Success rate: {stats.get('success_rate', 0):.1f}%")
            print(f"   Uptime: {stats.get('uptime', 0):.1f}s")

async def main():
    """Main test function"""
    async with ASRTester() as tester:
        results = await tester.run_all_tests()
        tester.print_summary(results)

        # Save results to file
        with open("asr_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to 'asr_test_results.json'")

if __name__ == "__main__":
    print("EmoRobCare ASR Service Test Suite")
    print("==================================")
    print("Make sure the ASR service is running on http://localhost:8001")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()