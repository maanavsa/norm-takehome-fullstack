import { useState } from 'react';
import { Box, Button, FormControl, FormLabel, Input, Textarea, VStack, Text, Spinner, Alert, AlertIcon, List, ListItem, Heading, Badge, Divider } from '@chakra-ui/react';

interface Citation {
  source: string;
  text: string;
}

interface Output {
  query: string;
  response: string;
  citations: Citation[];
}

export default function LegalQueryForm() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<Output | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const url = `http://localhost:80/query?query=${encodeURIComponent(query)}`;
      const res = await fetch(url, {
        method: 'GET',
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to fetch');
      }
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Function to render response text with styled citation numbers
  const renderResponseWithCitations = (response: string) => {
    // Split the response by citation patterns like [1], [2], etc.
    const parts = response.split(/(\[\d+\])/);
    
    return parts.map((part, index) => {
      const citationMatch = part.match(/\[(\d+)\]/);
      if (citationMatch) {
        const citationNumber = citationMatch[1];
        return (
          <Badge
            key={index}
            as="span"
            colorScheme="purple"
            variant="outline"
            fontSize="xs"
            px={1}
            py={0.5}
            borderRadius="sm"
            cursor="pointer"
            _hover={{ bg: "purple.50" }}
            transition="all 0.2s"
          >
            [{citationNumber}]
          </Badge>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Function to clean citation text by removing redundant source references
  const cleanCitationText = (text: string) => {
    // Remove patterns like "source 2", "Source 2", "source2", etc.
    let cleaned = text.replace(/\b(?:source|Source)\s*\d+\b/g, '').trim();
    // Remove leading colons and extra whitespace that might be left behind
    cleaned = cleaned.replace(/^:\s*/, '').trim();
    return cleaned;
  };

  return (
    <Box maxW="2xl" mx="auto" mt={10} p={6} bg="white" borderRadius="md" boxShadow="md">
      <form onSubmit={handleSubmit}>
        <VStack spacing={4} align="stretch">
          <FormControl isRequired>
            <FormLabel>Ask a legal question</FormLabel>
            <Textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="e.g. What happens if I steal?"
              size="md"
              minH="80px"
              disabled={loading}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e as any);
                }
              }}
            />
          </FormControl>
          <Button type="submit" colorScheme="purple" isLoading={loading} loadingText="Querying...">
            Submit
          </Button>
        </VStack>
      </form>
      {error && (
        <Alert status="error" mt={4} borderRadius="md">
          <AlertIcon />
          {error}
        </Alert>
      )}
      {result && (
        <Box mt={8}>
          <Heading as="h3" size="md" mb={4} color="purple.600">Response</Heading>
          <Box p={4} bg="gray.50" borderRadius="md" mb={6}>
            <Text lineHeight="1.6">
              {renderResponseWithCitations(result.response)}
            </Text>
          </Box>
          {result.citations && result.citations.length > 0 && (
            <Box>
              <Divider mb={4} />
              <Heading as="h4" size="sm" mb={3} color="gray.700">
                Sources & Citations
              </Heading>
              <VStack spacing={3} align="stretch">
                {result.citations.map((c, i) => (
                  <Box key={i} p={3} bg="white" border="1px solid" borderColor="gray.200" borderRadius="md" _hover={{ borderColor: "purple.200", boxShadow: "sm" }} transition="all 0.2s">
                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                      <Badge colorScheme="purple" variant="solid" fontSize="xs" borderRadius="full" minW="20px" textAlign="center">
                        {i + 1}
                      </Badge>
                      <Text fontSize="sm" fontWeight="medium" color="gray.800">
                        {c.source}
                      </Text>
                    </Box>
                    <Text fontSize="sm" color="gray.700" lineHeight="1.5" pl={7}>
                      {cleanCitationText(c.text)}
                    </Text>
                  </Box>
                ))}
              </VStack>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
} 