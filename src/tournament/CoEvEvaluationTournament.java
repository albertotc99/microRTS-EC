package tournament;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import ai.core.AI;
import myAgent.MyAgent;
import rts.units.UnitTypeTable;
import tournaments.RoundRobinTournament;

public class CoEvEvaluationTournament {

  public static void main(String[] args) {
    List<AI> agents = new ArrayList<>();
    UnitTypeTable utt = new UnitTypeTable();
    
    // Ruta del fichero
    String filePath = args[0];
        
    // Crear un objeto File con la ruta especificada
    File csvFile = new File(filePath);
    
    // Comprobar si el fichero existe
    if (csvFile.exists()) {
        String line = "";
        String csvSeparator = ",";

        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            while ((line = br.readLine()) != null) {
                // Divide la línea en valores usando el separador
                String[] values = line.split(csvSeparator);
                MyAgent agent = checkMyAgent(values);
                agents.add(agent);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    } else {
        System.out.println("El fichero no existe.");
        System.exit(0);
    }

    String [] mapsString = {
        // "maps/melee14x12Mixed18.xml",
        "maps/16x16/basesWorkers16x16A.xml",
        // "maps/basesWorkers32x32A.xml",
        "maps/barricades24x24.xml",
        // "maps/8x8/FourBasesWorkers8x8.xml",
        // "maps/16x16/TwoBasesBarracks16x16.xml",
        // "maps/NoWhereToRun9x8.xml",
        // "maps/chambers32x32.xml",
        //"maps/GardenOfWar64x64.xml",
        "maps/BroodWar/(2)Benzene.scxA.xml",
        // "maps/BroodWar/(2)Destination.scxA.xml",
        // "maps/BroodWar/(4)Andromeda.scxB.xml"
    };
    List<String> maps = Arrays.asList(mapsString);
    int iterations = 2;
    int maxGameLength = 5000;
    int timeBudget = 100;
    int iterationsBudget = -1;
    int preAnalysisBudget = 0;
    boolean fullObservability = true;
    boolean timeOutCheck = true;
    boolean gcCheck = true;
    boolean selfMatches = true;
    boolean preGameAnalysis = preAnalysisBudget > 0;
    String folder = "./FirstExecCoEvGA";

    // Crear un objeto File con la ruta especificada
    File directory = new File(folder);
    if (!directory.exists()) {
      directory.mkdirs();
    }

    String prefix = folder + "/tournament_";
    int idx = 0;
    File file;
    do {
        idx++;
        file = new File(prefix + idx);
    }while(file.exists());
    file.mkdir();
    String tournamentfolder = file.getPath();
    final File fileToUse = new File(tournamentfolder + "/tournament.csv");
    final String tracesFolder = null;// (tournamentfolder + "/traces");

    try {
      System.out.print(tournamentfolder + "/tournament.csv");
      Writer writer = new FileWriter(fileToUse);
      new RoundRobinTournament(agents).runTournament(-1, maps,
                                          iterations, maxGameLength, timeBudget, iterationsBudget, 
                                          preAnalysisBudget, 1000, // 1000 is just to give 1 second to the AIs to load their read/write folder saved content
                                          fullObservability, selfMatches, timeOutCheck, gcCheck, preGameAnalysis, 
                                          utt, tracesFolder,
                                          writer, null,
                                          tournamentfolder);

      writer.close();
    } catch (Exception e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    
  }

  private static MyAgent checkMyAgent(String[] args){
    // Parsear los parámetros 
    double[] doubleParams = new double[8];
    int[] intParams = new int[2];
    UnitTypeTable utt = new UnitTypeTable();    
    MyAgent agent = new MyAgent(utt);

    if (args.length != 10) {
      System.err.println("Debe proporcionar exactamente 10 parámetros.");
      // System.exit(1);
      agent = new MyAgent(utt, 0.2, 0.82, 0.85, 3, 0, 0.7, 0.4, 0.3, 0.12, 0.25);
      // agent = new MyAgent(utt, 0.2, 0.95, 0.9, 3, 0, 0.3, 0.4, 0.3, 0.08, 0.1);
      // agent = new MyAgent(utt, 0.2, 1, 0.8, 3, 20, 0, 0, 0, 0.08, 0.1);

    } else {
      try {
        // Verify and assign the first 3 doubles
        for (int i = 0; i < 3; i++) {
            doubleParams[i] = Double.parseDouble(args[i].strip());
            if (doubleParams[i] < 0.0 || doubleParams[i] > 1.0) {
                throw new IllegalArgumentException("Todos los parámetros double deben estar entre 0 y 1.");
            }
        }

        // Verify and assign 2 integers
        for (int i = 0; i < 2; i++) {
            intParams[i] = Integer.parseInt(args[i + 3].strip());
            if (intParams[i] > 30 || intParams[i] < 0) {
                throw new IllegalArgumentException("Todos los parámetros int deben estar entre 0 y 30.");
            }
        }

        // Verifify and assign 5 last doubles
        for (int i = 0; i < 5; i++) {
            doubleParams[i + 3] = Double.parseDouble(args[i + 5].strip());
            if (doubleParams[i + 3] < 0.0 || doubleParams[i + 3] > 1.0) {
                throw new IllegalArgumentException("Todos los parámetros double deben estar entre 0 y 1.");
            }
        }

      } catch (NumberFormatException e) {
          System.err.println("Todos los parámetros deben ser números.");
          System.exit(1);
      } catch (IllegalArgumentException e) {
          System.err.println(e.getMessage());
          System.exit(1);
      }
 
      agent = new MyAgent(utt, doubleParams[0], doubleParams[1], doubleParams[2], 
                intParams[0], intParams[1], 
                doubleParams[3], doubleParams[4], doubleParams[5], 
                doubleParams[6], doubleParams[7]);
    }

    return (MyAgent) agent;
  }

}
