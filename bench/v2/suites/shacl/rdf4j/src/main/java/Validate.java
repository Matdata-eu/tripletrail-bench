import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.file.Path;

import org.eclipse.rdf4j.model.Model;
import org.eclipse.rdf4j.model.vocabulary.RDF4J;
import org.eclipse.rdf4j.repository.RepositoryException;
import org.eclipse.rdf4j.repository.sail.SailRepository;
import org.eclipse.rdf4j.repository.sail.SailRepositoryConnection;
import org.eclipse.rdf4j.rio.RDFFormat;
import org.eclipse.rdf4j.rio.Rio;
import org.eclipse.rdf4j.sail.memory.MemoryStore;
import org.eclipse.rdf4j.sail.shacl.ShaclSail;
import org.eclipse.rdf4j.sail.shacl.ShaclSailValidationException;

/**
 * Validates a data file against a shapes file with RDF4J's ShaclSail on a memory store, the way
 * an application would: the shapes go into the shapes graph, then the data is added in one
 * transaction whose commit validates it (bulk validation).
 *
 * <pre>java -jar rdf4j-shacl-validate.jar &lt;data.nt or .ttl&gt; &lt;shapes.ttl&gt; &lt;report.ttl&gt;</pre>
 *
 * Exits 0 when the data conforms, 1 when it does not (the report is written), 2 on an error.
 */
public class Validate {
  static RDFFormat format(String file) {
    return Rio.getParserFormatForFileName(file).orElse(RDFFormat.TURTLE);
  }

  public static void main(String[] args) throws Exception {
    ShaclSail shacl = new ShaclSail(new MemoryStore());
    shacl.setDashDataShapes(true);
    shacl.setEclipseRdf4jShaclExtensions(true);
    SailRepository repo = new SailRepository(shacl);
    long t0 = System.nanoTime();
    try (SailRepositoryConnection c = repo.getConnection()) {
      c.begin();
      c.add(Path.of(args[1]).toFile(), null, format(args[1]), RDF4J.SHACL_SHAPE_GRAPH);
      c.commit();
      System.err.printf("loaded the shapes in %.1f s%n", (System.nanoTime() - t0) / 1e9);
      long t1 = System.nanoTime();
      c.begin(ShaclSail.TransactionSettings.ValidationApproach.Bulk);
      c.add(Path.of(args[0]).toFile(), null, format(args[0]));
      try {
        c.commit();
        try (OutputStream out = new FileOutputStream(args[2])) {
          out.write(("@prefix sh: <http://www.w3.org/ns/shacl#> .\n"
              + "[] a sh:ValidationReport ; sh:conforms true .\n").getBytes());
        }
        System.err.printf("conforms in %.1f s%n", (System.nanoTime() - t1) / 1e9);
      } catch (RepositoryException e) {
        if (!(e.getCause() instanceof ShaclSailValidationException v)) {
          throw e;
        }
        Model report = v.validationReportAsModel();
        try (OutputStream out = new FileOutputStream(args[2])) {
          Rio.write(report, out, RDFFormat.TURTLE);
        }
        System.err.printf("does not conform in %.1f s%n", (System.nanoTime() - t1) / 1e9);
        System.exit(1);
      }
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(2);
    } finally {
      repo.shutDown();
    }
  }
}
